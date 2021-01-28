#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_

#undef NBR_TABLE_CONF_MAX_NEIGHBORS
#undef UIP_CONF_MAX_ROUTES

/* configure number of neighbors and routes */
#define NBR_TABLE_CONF_MAX_NEIGHBORS     10
#define UIP_CONF_MAX_ROUTES   30

#undef NETSTACK_CONF_RDC
#define NETSTACK_CONF_RDC     nullrdc_driver
#undef NULLRDC_CONF_802154_AUTOACK
#define NULLRDC_CONF_802154_AUTOACK       1

/* Define as minutes */
#define RPL_CONF_DEFAULT_LIFETIME_UNIT   60

/* 10 minutes lifetime of routes */
#define RPL_CONF_DEFAULT_LIFETIME        10

#define RPL_CONF_DEFAULT_ROUTE_INFINITE_LIFETIME 1


/* Use RPL metric containers */
#define RPL_CONF_WITH_MC 1
/* Use the new distance based metric */
#define RPL_CONF_DAG_MC RPL_DAG_MC_X_POSITION

/* the default MIN_HOPRANKINC is too big for distance based RPL; reduce this to smaller value (10) */
#define RPL_CONF_MIN_HOPRANKINC 10

#endif
