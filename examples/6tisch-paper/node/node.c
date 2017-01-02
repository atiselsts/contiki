/*
 * Copyright (c) 2016, University of Bristol - http://www.bristol.ac.uk
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
 * COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */
/*---------------------------------------------------------------------------*/
#include "contiki.h"
#include "net/netstack.h"
#include "net/ipv6/uip-ds6.h"
#include "tsch.h"
#include "simple-udp.h"
#include "lib/random.h"
#include "powertrace.h"

#define DEBUG DEBUG_PRINT
#include "net/ip/uip-debug.h"

#include <stdio.h>
/*---------------------------------------------------------------------------*/
#define PACKETGEN_PERIOD (10 * CLOCK_SECOND)
#define PACKET_LENGTH  60
/*---------------------------------------------------------------------------*/

struct simple_udp_connection unicast_connection;

PROCESS(node_process, "Packet generator");
AUTOSTART_PROCESSES(&node_process);
/*---------------------------------------------------------------------------*/
const linkaddr_t *linkaddr_from_id(uint16_t id)
{
#if __MSP430__ /* Simulator */
  static const linkaddr_t receiver_addresses[] = {
    { { 0xc1, 0x0c, 0x0, 0x00, 0x00, 0x00, 0x00, 0x01 } }
  };
#else
  static const linkaddr_t receiver_addresses[] = {
    { { 0xc1, 0x0c, 0x0, 0x00, 0x00, 0x00, 0x00, 0x01 } }
  };
#endif

  return &receiver_addresses[id - 1];
}
/*---------------------------------------------------------------------------*/
static void
generate_packets(void)
{
  static uint16_t seqnum;
  static char buf[PACKET_LENGTH];
  uip_ipaddr_t ipaddr;

  seqnum++; /* increment message sequence number */

  printf("tx %u: %u\n", node_id, seqnum);

  memcpy(buf, &seqnum, sizeof(seqnum));

  uip_ip6addr(&ipaddr, NETWORK_PREFIX, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00);
  uip_ds6_set_addr_iid(&ipaddr, (uip_lladdr_t *)linkaddr_from_id(1));
  simple_udp_sendto(&unicast_connection, buf, sizeof(buf), &ipaddr);
}
/*---------------------------------------------------------------------------*/
static void
print_stats(void)
{
  int i;
  uint8_t state;
  uip_ds6_defrt_t *default_route;
  uip_ds6_route_t *route;

  PRINTA("--- Network status ---\n");

  /* Our IPv6 addresses */
  PRINTA("-- Server IPv6 addresses:\n");
  for(i = 0; i < UIP_DS6_ADDR_NB; i++) {
    state = uip_ds6_if.addr_list[i].state;
    if(uip_ds6_if.addr_list[i].isused &&
       (state == ADDR_TENTATIVE || state == ADDR_PREFERRED)) {
      PRINTA("-- ");
      uip_debug_ipaddr_print(&uip_ds6_if.addr_list[i].ipaddr);
      PRINTA("\n");
    }
  }

  /* Our default route */
  PRINTA("-- Default route:\n");
  default_route = uip_ds6_defrt_lookup(uip_ds6_defrt_choose());
  if(default_route != NULL) {
    PRINTA("-- ");
    uip_debug_ipaddr_print(&default_route->ipaddr);
    PRINTA(" (lifetime: %lu seconds)\n", (unsigned long)default_route->lifetime.interval);
  } else {
    PRINTA("-- None\n");
  }

  /* Our routing entries */
  PRINTA("-- Routing entries (%u in total):\n", uip_ds6_route_num_routes());
  route = uip_ds6_route_head();
  while(route != NULL) {
    PRINTA("-- ");
    uip_debug_ipaddr_print(&route->ipaddr);
    PRINTA(" via ");
    uip_debug_ipaddr_print(uip_ds6_route_nexthop(route));
    PRINTA(" (lifetime: %lu seconds)\n", (unsigned long)route->state.lifetime);
    route = uip_ds6_route_next(route);
  }

  PRINTA("----------------------\n");
}
/*---------------------------------------------------------------------------*/
static void
init_net(void)
{
  uip_ipaddr_t ipaddr;
  const linkaddr_t *lla;
  uip_ds6_nbr_t *nbr;

  uip_ip6addr(&ipaddr, NETWORK_PREFIX, 0, 0, 0, 0, 0, 0, 0);
  uip_ds6_set_addr_iid(&ipaddr, &uip_lladdr);
  uip_ds6_addr_add(&ipaddr, 0, ADDR_AUTOCONF);

  lla = linkaddr_from_id(1);
  uip_ip6addr(&ipaddr, NETWORK_PREFIX, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00);
  uip_ds6_set_addr_iid(&ipaddr, (uip_lladdr_t *)lla);

  /* add a link-layer neighbor */
  nbr = uip_ds6_nbr_add(&ipaddr, (uip_lladdr_t *)lla, 1 /* isrouter */,
      NBR_REACHABLE, NBR_TABLE_REASON_MAC, NULL);

  /* set the neighbor timer to never expire */
  // stimer_set(&nbr->reachable, (unsigned long)(0xffffffff / 2));

  /* add a route, nexthop through itself */
  uip_ds6_route_add(&ipaddr, 128, &ipaddr); 
}
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(node_process, ev, data)
{
  static struct etimer et;
  static struct etimer packet_timer;
  static uint16_t n;

  PROCESS_BEGIN();

  PRINTF("6tisch test sender starting\n");

#if USE_ENERGEST
  /* Start powertracing, once every minute */
  powertrace_start(CLOCK_SECOND * 60);
#endif

  init_net();
  
  /* turn on TSCH */
  NETSTACK_MAC.on();

  simple_udp_register(&unicast_connection, APP_UDP_PORT,
      NULL, APP_UDP_PORT, NULL);

  /* initial timeout: allow the network to start */
  etimer_set(&et, 30 * CLOCK_SECOND);

  while(1) {
    PROCESS_YIELD();
    if(ev == PROCESS_EVENT_TIMER) {
      if(data == &et) {
        etimer_set(&et, PACKETGEN_PERIOD);
        etimer_set(&packet_timer, 10 + random_rand() % (PACKETGEN_PERIOD - 10));
        n++;
        if((n % 60) == 0) {
          print_stats();
        }
      }
      else if(data == &packet_timer) {
        generate_packets();
      }
    }
  }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
