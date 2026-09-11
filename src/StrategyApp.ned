package smarthome;

import inet.applications.udpapp.UdpBasicApp;

// Behavioral strategy comparison over UDP, not full CoAP or MQTT.
simple StrategyApp extends UdpBasicApp
{
    parameters:
        @class(StrategyApp);
        string role;
        double eventStart @unit(s) = default(1s);
        double eventInterval @unit(s) = default(10s);
        int requestBytes = default(20);
        @signal[eventLatency](type=double);
        @signal[roundTripTime](type=double);
        @signal[deliveryDelay](type=double);
        @statistic[eventLatency](unit=s; record=stats);
        @statistic[roundTripTime](unit=s; record=stats);
        @statistic[deliveryDelay](unit=s; record=stats);
}
