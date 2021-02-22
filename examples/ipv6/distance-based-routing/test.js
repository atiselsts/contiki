GENERATE_MSG(5000, "next node goes into bin");

while(true) {
    log.log(time + ":" + id + ":" + msg + "\n");

    if(msg.equals("next node goes into bin")) {
        // move the root up
        var m = sim.getMoteWithID(1);
        var x = m.getInterfaces().getPosition().getXCoordinate();
        var y = m.getInterfaces().getPosition().getYCoordinate();
        m.getInterfaces().getPosition().setCoordinates(x+1, y+1, 0);
        log.log("setting root pos to " + m.getInterfaces().getPosition().getXCoordinate() + " " + m.getInterfaces().getPosition().getYCoordinate() + "\n");
        GENERATE_MSG(5000, "next node goes into bin");
    }

    YIELD();
}
