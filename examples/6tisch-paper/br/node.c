/*
 * Copyright (c) 2016, University of Bristol - http://www.bris.ac.uk/
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
#include "net/ip/uip.h"
#include "net/ipv6/uip-ds6.h"
#include "net/ipv6/uip-ds6-route.h"
#include "net/rpl/rpl.h"
#include "net/mac/mac.h"
#include "sys/node-id.h"
#include "simple-udp.h"
#include "tsch.h"
#include "tsch-schedule.h"
#include "powertrace.h"

#define DEBUG DEBUG_PRINT
#include "net/ip/uip-debug.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/*---------------------------------------------------------------------------*/
struct simple_udp_connection unicast_connection;

PROCESS(receiver_process, "Receiver");
AUTOSTART_PROCESSES(&receiver_process);
/*---------------------------------------------------------------------------*/
static void
receiver(struct simple_udp_connection *c,
         const uip_ipaddr_t *sender_addr,
         uint16_t sender_port,
         const uip_ipaddr_t *receiver_addr,
         uint16_t receiver_port,
         const uint8_t *data,
         uint16_t datalen)
{
  uint16_t seqnum;
  linkaddr_t sender_lladdr;

  memcpy(&sender_lladdr, &sender_addr->u8[8], sizeof(sender_lladdr));
  /* change the first octet as per RFC */
  sender_lladdr.u8[0] ^= 2;

  memcpy(&seqnum, data, sizeof(seqnum));

  printf("rx %u: %u\n", LOG_ID_FROM_LINKADDR(&sender_lladdr), seqnum);
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
void
net_init(void)
{
  int i, sf_handle;
  uip_ipaddr_t ipaddr;

  uip_ip6addr(&ipaddr, NETWORK_PREFIX, 0, 0, 0, 0, 0, 0, 0);
  uip_ds6_set_addr_iid(&ipaddr, &uip_lladdr);
  uip_ds6_addr_add(&ipaddr, 0, ADDR_AUTOCONF);

  NETSTACK_MAC.on();

  #if USE_TSCH_WITH_DEDICATED_SLOTS
    /* First slotframe: only listen slot for each node. Start at node_id == 2, because 1 is the coordinator */
    sf_handle = 0;
    struct tsch_slotframe *sf_unicast = tsch_schedule_add_slotframe(sf_handle, TSCH_SCHEDULE_CONF_DEFAULT_LENGTH);
    for(i = 2; i < 2 + DEF_LEAVES_COUNT; i++) {
      tsch_schedule_add_link(sf_unicast,
          LINK_OPTION_RX,
          LINK_TYPE_NORMAL, &tsch_broadcast_address,
          i, sf_handle);
    }

    /* Second slotframe: single Tx slot for EBs, at coordinator only */
    sf_handle = 1;
    struct tsch_slotframe *sf_eb = tsch_schedule_add_slotframe(sf_handle, 397);
    tsch_schedule_add_link(sf_eb,
        LINK_OPTION_TX,
        LINK_TYPE_ADVERTISING_ONLY, &tsch_broadcast_address,
        0, sf_handle);

  #endif /* USE_TSCH_WITH_DEDICATED_SLOTS */
}
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(receiver_process, ev, data)
{
  static struct etimer et;

  PROCESS_BEGIN();

  PRINTF("6tisch test receiver starting\n");

#if USE_ENERGEST
  /* Start powertracing, once every minute */
  powertrace_start(CLOCK_SECOND * 60);
#endif

  /* configure TSCH (if enabled as the MAC protocol) in coordinator mode */
  tsch_set_coordinator(1);

  simple_udp_register(&unicast_connection, APP_UDP_PORT,
                      NULL, APP_UDP_PORT, receiver);

  net_init();

  /* initial timeout: allow the network to start */
  etimer_set(&et, DEF_STARTUP_DELAY * CLOCK_SECOND);
  PROCESS_WAIT_UNTIL(etimer_expired(&et));
  /* Nodes present at startup should have joined. Now send fewer EBs */
  tsch_set_eb_period(TSCH_CONF_MAX_EB_PERIOD);

  /* Print out stats every minute */
  etimer_set(&et, CLOCK_SECOND * 60);

  while(1) {
    PROCESS_WAIT_EVENT();
    if(etimer_expired(&et)) {
      print_stats();
      etimer_reset(&et);
    }
  }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
