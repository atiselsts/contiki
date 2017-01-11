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
#include "net/packetbuf.h"
#if USE_TSCH
#include "tsch.h"
#include "tsch-schedule.h"
#endif
#include "lib/random.h"
#include "sys/node-id.h"

#define DEBUG DEBUG_PRINT
#include "net/ip/uip-debug.h"

#include <stdio.h>
/*---------------------------------------------------------------------------*/
#define PACKETGEN_PERIOD CLOCK_SECOND
/* Up to 125 byte total packet, inluding MAC-layer headers;
 * 99 was selected as the maximal payload working in all configurations.
 */
#define PACKET_LENGTH  98

/*---------------------------------------------------------------------------*/
#if !USE_TSCH
const linkaddr_t tsch_broadcast_address = { { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff } };
/* Address used for the EB virtual neighbor queue */
const linkaddr_t tsch_eb_address = { { 0, 0, 0, 0, 0, 0, 0, 0 } };
#endif
/*---------------------------------------------------------------------------*/

PROCESS(node_process, "Packet generator");
AUTOSTART_PROCESSES(&node_process);
/*---------------------------------------------------------------------------*/
// const linkaddr_t *linkaddr_from_id(uint16_t id)
// {
// #if __MSP430__ /* Simulator */
//   static const linkaddr_t receiver_addresses[] = {
//     { { 0xc1, 0x0c, 0x0, 0x00, 0x00, 0x00, 0x00, 0x01 } }
//   };
// #else
//   static const linkaddr_t receiver_addresses[] = {
//     { { 0xc1, 0x0c, 0x0, 0x00, 0x00, 0x00, 0x00, 0x01 } }
// /*    { { 0x00, 0x12, 0x4B, 0x00, 0x06, 0x0D, 0xB3, 0x65 } } */
//   };
// #endif

//   return &receiver_addresses[id - 1];
// }
/*---------------------------------------------------------------------------*/
static void
generate_packets(void)
{
  static uint16_t seqnum;
  static char buf[PACKET_LENGTH];
  uip_ipaddr_t ipaddr;

  seqnum++; /* increment message sequence number */

#if USE_TSCH
#if TSCH_LOG_CONF_LEVEL > 0
  printf("tx %u: %u\n", node_id, seqnum);
#endif
#endif

  memcpy(buf, &seqnum, sizeof(seqnum));

  // uip_ip6addr(&ipaddr, NETWORK_PREFIX, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00);
  // uip_ds6_set_addr_iid(&ipaddr, (uip_lladdr_t *)linkaddr_from_id(1));

  packetbuf_copyfrom(buf, sizeof(buf));
  packetbuf_set_addr(PACKETBUF_ADDR_RECEIVER, address_from_node_id(1));
#if !USE_TSCH
  packetbuf_set_attr(PACKETBUF_ATTR_FRAME_TYPE, FRAME802154_DATAFRAME);
#if WITH_SECURITY
  /* set same level as for TSCH data */
  packetbuf_set_attr(PACKETBUF_ATTR_SECURITY_LEVEL, 0x5);
#endif
#endif /* !USE_TSCH */
  NETSTACK_MAC.send(NULL, NULL);
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

  lla = address_from_node_id(1);
  uip_ip6addr(&ipaddr, NETWORK_PREFIX, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00);
  uip_ds6_set_addr_iid(&ipaddr, (uip_lladdr_t *)lla);

  /* add a link-layer neighbor */
  nbr = uip_ds6_nbr_add(&ipaddr, (uip_lladdr_t *)lla, 1 /* isrouter */,
      NBR_REACHABLE, NBR_TABLE_REASON_MAC, NULL);

  /* set the neighbor timer to never expire */
  (void)nbr;
  // stimer_set(&nbr->reachable, (unsigned long)(0xffffffff / 2));

  /* add a route, nexthop through itself */
  uip_ds6_route_add(&ipaddr, 128, &ipaddr); 
}
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(node_process, ev, data)
{
  static struct etimer et;

  PROCESS_BEGIN();

  PRINTF("6tisch test sender starting\n");

  init_net();

  frame802154_set_pan_id(IEEE802154_CONF_PANID);

  /* turn on TSCH */
  NETSTACK_MAC.on();

  /* initial timeout: allow the network to start */
  etimer_set(&et, STARTUP_DELAY * CLOCK_SECOND);
  PROCESS_WAIT_UNTIL(etimer_expired(&et));

#if USE_TSCH
  /* Nodes present at startup should have joined. Now send no EBs */
  tsch_set_eb_period(0);
#endif

  printf("generating packets\n");

  etimer_set(&et, PACKETGEN_PERIOD);

  while(1) {
    PROCESS_YIELD();
    if(ev == PROCESS_EVENT_TIMER && data == &et) {
      generate_packets();
      etimer_reset(&et);
    }
  }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
