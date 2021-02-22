all: udp-client udp-server
CONTIKI=../../..

CFLAGS += -DPROJECT_CONF_H=\"project-conf.h\"

TARGET_LIBFILES += -lm

CONTIKI_WITH_IPV6 = 1
include $(CONTIKI)/Makefile.include
