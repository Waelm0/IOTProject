package smarthome.simulations;

import inet.node.inet.SensorNode;
import inet.node.inet.StandardHost;
import inet.node.ethernet.Eth100M;
import inet.physicallayer.wireless.ieee802154.packetlevel.Ieee802154NarrowbandScalarRadioMedium;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.visualizer.contract.IIntegratedVisualizer;
import inet.node.inet.Router;

module IoTGateway extends Router
{
    parameters:
        @display("i=device/accesspoint");
        numWlanInterfaces = 1;
        hasUdp = default(true);
    submodules:
    connections allowunconnected:
}

network SmartHomeNetwork
{
    parameters:
        int numTempHumidity = default(4);
        int numOccupancyMotion = default(4);
        int numSmokeEnv = default(4);
        int numActuators = default(3);
        @display("bgb=900,600");
    submodules:
        // --- Constrained (802.15.4) side ---
        tempHumiditySensor[numTempHumidity]: SensorNode {
            @display("p=150,100");
        }
        occupancyMotionSensor[numOccupancyMotion]: SensorNode {
            @display("p=150,250");
        }
        smokeEnvSensor[numSmokeEnv]: SensorNode {
            @display("p=150,380");
        }
        actuator[numActuators]: SensorNode {
            @display("p=150,480");
        }
        gateway: IoTGateway {
            @display("p=400,280");
        }

        // --- Core / IP side ---
        monitoringApp: StandardHost {
            @display("p=700,280");
        }

        // --- Supporting infrastructure ---
        radioMedium: Ieee802154NarrowbandScalarRadioMedium {
            @display("p=834,48");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=815,527");
        }
        visualizer: <default("IntegratedCanvasVisualizer")> like IIntegratedVisualizer {
            @display("p=700,50");
        }

    connections:
        gateway.ethg++ <--> Eth100M <--> monitoringApp.ethg++;
}
