#include <cstdio>
#include <set>
#include "inet/common/SimpleModule.h"
#include "inet/networklayer/common/L3AddressResolver.h"
#include "inet/networklayer/contract/IInterfaceTable.h"
#include "inet/networklayer/ipv6/Ipv6InterfaceData.h"
#include "inet/networklayer/ipv6/Ipv6RoutingTable.h"

using namespace inet;

class SmartHomeIpv6Configurator : public SimpleModule
{
  protected:
    int numInitStages() const override { return NUM_INIT_STAGES; }
    std::set<std::string> assignedAddresses;

    void configure(cModule *node, const char *interfaceName, const char *address,
                   const char *prefix, const char *defaultGateway = nullptr)
    {
        if (!node || node->par("hasIpv4").boolValue() || !node->par("hasIpv6").boolValue())
            throw cRuntimeError("Static IPv6 configuration requires IPv6-only nodes");
        auto table = L3AddressResolver().interfaceTableOf(node);
        auto interface = table->findInterfaceByName(interfaceName);
        auto routes = L3AddressResolver().findIpv6RoutingTableOf(node);
        if (!interface || !routes)
            throw cRuntimeError("Missing IPv6 routing table or interface %s on %s",
                                interfaceName, node->getFullPath().c_str());
        if (!assignedAddresses.insert(address).second)
            throw cRuntimeError("Duplicate IPv6 address: %s", address);

        auto data = interface->getProtocolDataForUpdate<Ipv6InterfaceData>();
        // Addresses are centrally provisioned, so SLAAC/DAD startup is not modeled.
        // INET still performs neighbor resolution and reachability detection.
        data->setAdvSendAdvertisements(false);
        auto linkLocal = data->getLinkLocalAddress();
        if (linkLocal.isUnspecified())
            data->assignAddress(Ipv6Address::formLinkLocalAddress(interface->getInterfaceToken()),
                                false, SIMTIME_ZERO, SIMTIME_ZERO);
        else
            data->permanentlyAssign(linkLocal);
        data->assignAddress(Ipv6Address(address), false, SIMTIME_ZERO, SIMTIME_ZERO);
        routes->addStaticRoute(Ipv6Address(prefix), 64, interface->getInterfaceId(),
                               Ipv6Address::UNSPECIFIED_ADDRESS);
        if (defaultGateway)
            routes->addStaticRoute(Ipv6Address::UNSPECIFIED_ADDRESS, 0,
                                   interface->getInterfaceId(), Ipv6Address(defaultGateway));
    }

    void initialize(int stage) override
    {
        SimpleModule::initialize(stage);
        if (stage != INITSTAGE_STATIC_ROUTING)
            return;
        auto network = getParentModule();
        auto gateway = network->getSubmodule("gateway");
        configure(gateway, "wlan0", "2001:db8:1::1", "2001:db8:1::");
        configure(gateway, "eth0", "2001:db8:2::1", "2001:db8:2::");
        if (!gateway->par("forwarding").boolValue())
            throw cRuntimeError("Gateway must forward IPv6 packets");
        configure(network->getSubmodule("monitoringApp"), "eth0", "2001:db8:2::2",
                  "2001:db8:2::", "2001:db8:2::1");

        const char *families[] = {"tempHumiditySensor", "occupancyMotionSensor",
                                  "smokeEnvSensor", "actuator"};
        for (unsigned int family = 0; family < 4; ++family) {
            int count = network->getSubmoduleVectorSize(families[family]);
            if (count > 65535)
                throw cRuntimeError("Too many nodes for the configured IPv6 address plan");
            for (int i = 0; i < count; ++i) {
                char address[64];
                std::snprintf(address, sizeof(address), "2001:db8:1::%x:%x", family + 1, i + 1);
                configure(network->getSubmodule(families[family], i), "wlan0", address,
                          "2001:db8:1::", "2001:db8:1::1");
            }
        }
    }

    void handleMessage(cMessage *message) override
    {
        throw cRuntimeError("IPv6 configurator does not process messages");
    }
};

Define_Module(SmartHomeIpv6Configurator);
