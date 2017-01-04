/* A simple log file generator script */

//TIMEOUT(10000);

//TIMEOUT(1805000); // 1800000 msec = 30 minutes
TIMEOUT(605000); // 660000 msec = 10 minutes
//TIMEOUT(185000); // 3 minutes

timeout_function = function () {
    log.log("Script timed out.\n");
    log.testOK();
}

if (msg) {
    log.log("> " + time + ":" + id + ":" + msg + "\n");
}

while (true) {
    YIELD();

    log.log("> " + time + ":" + id + ":" + msg + "\n");
}
