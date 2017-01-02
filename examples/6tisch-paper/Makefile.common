CONTIKI_PROJECT = node
all: $(CONTIKI_PROJECT)

CONTIKI=../../..
CFLAGS += -DPROJECT_CONF_H=\"project-conf.h\"

CFLAGS += -DUSE_ENERGEST=1 -DENERGEST_CONF_ON=1

CONTIKI_WITH_IPV6 = 1

# don't use RPL
CONTIKI_WITH_RPL = 0

MAKE_WITH_ORCHESTRA ?= 0 # force Orchestra from command line
MAKE_WITH_SECURITY ?= 0 # force Security from command line

#APPS += orchestra
MODULES += core/net/mac/tsch

APPS += powertrace-cc26xx

ifeq ($(MAKE_WITH_ORCHESTRA),1)
CFLAGS += -DWITH_ORCHESTRA=1
endif

ifeq ($(MAKE_WITH_SECURITY),1)
CFLAGS += -DWITH_SECURITY=1
endif

include $(CONTIKI)/Makefile.include
