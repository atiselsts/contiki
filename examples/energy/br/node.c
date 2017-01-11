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
#if USE_TSCH
#include "tsch.h"
#include "tsch-schedule.h"
#endif

#define DEBUG DEBUG_PRINT
#include "net/ip/uip-debug.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/*---------------------------------------------------------------------------*/
#if !USE_TSCH
const linkaddr_t tsch_broadcast_address = { { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff } };
/* Address used for the EB virtual neighbor queue */
const linkaddr_t tsch_eb_address = { { 0, 0, 0, 0, 0, 0, 0, 0 } };
#endif
/*---------------------------------------------------------------------------*/
PROCESS(receiver_process, "BR");
AUTOSTART_PROCESSES(&receiver_process);
/*---------------------------------------------------------------------------*/
void
net_init(void)
{
  uip_ipaddr_t ipaddr;

  uip_ip6addr(&ipaddr, NETWORK_PREFIX, 0, 0, 0, 0, 0, 0, 0);
  uip_ds6_set_addr_iid(&ipaddr, &uip_lladdr);
  uip_ds6_addr_add(&ipaddr, 0, ADDR_AUTOCONF);

  NETSTACK_MAC.on();
}
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(receiver_process, ev, data)
{
  static struct etimer et;

  PROCESS_BEGIN();

  PRINTF("6tisch test BR starting\n");

#if USE_TSCH
  /* configure TSCH (if enabled as the MAC protocol) in coordinator mode */
  tsch_set_coordinator(1);
#endif

  frame802154_set_pan_id(IEEE802154_CONF_PANID);

  net_init();

  /* initial timeout: allow the network to start */
  etimer_set(&et, DEF_STARTUP_DELAY * CLOCK_SECOND);
  PROCESS_WAIT_UNTIL(etimer_expired(&et));

  printf("disabling EBs\n");

#if USE_TSCH
  /* Nodes present at startup should have joined. Now send no EBs */
  tsch_set_eb_period(0);
#endif

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
