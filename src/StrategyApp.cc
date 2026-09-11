#include <cmath>
#include <map>
#include "inet/applications/udpapp/UdpBasicApp.h"
#include "inet/applications/base/ApplicationPacket_m.h"
#include "inet/common/TimeTag_m.h"
#include "inet/networklayer/common/L3AddressResolver.h"
#include "inet/networklayer/common/L3AddressTag_m.h"
#include "inet/transportlayer/common/L4PortTag_m.h"

using namespace inet;

class StrategyApp : public UdpBasicApp
{
  protected:
    std::map<int, int> lastEvent;
    int observed = 0;
    void transmit(const char *name, const L3Address& destination, int port,
                  int bytes, double requestTime, double eventTime, int origin, int event)
    {
        auto packet = new Packet(name);
        auto payload = makeShared<ApplicationPacket>();
        payload->setChunkLength(B(bytes));
        payload->setSequenceNumber(numSent);
        payload->addTag<CreationTimeTag>()->setCreationTime(simTime());
        packet->insertAtBack(payload);
        // Metadata models fields inside the declared application payload.
        packet->addPar("requestTime") = requestTime;
        packet->addPar("eventTime") = eventTime;
        packet->addPar("origin") = origin;
        packet->addPar("event") = event;
        emit(packetSentSignal, packet);
        socket.sendTo(packet, destination, port);
        numSent++;
    }
    void sendPacket() override
    {
        std::string role = par("role").stdstringValue();
        if (role == "poller")
            transmit("PollRequest", chooseDestAddr(), destPort, par("requestBytes"), simTime().dbl(), 0, -1, -1);
        else if (role == "publisher") {
            int event = numSent;
            transmit("Publish", chooseDestAddr(), destPort, par("messageLength"), -1,
                simTime().dbl(), getParentModule()->getIndex(), event);
        }
        else
            throw cRuntimeError("Only poller and publisher may have scheduled sends");
    }
    void processPacket(Packet *packet) override
    {
        emit(packetReceivedSignal, packet);
        numReceived++;
        std::string role = par("role").stdstringValue();
        double requestTime = packet->par("requestTime").doubleValue();
        double eventTime = packet->par("eventTime").doubleValue();
        int origin = packet->par("origin").longValue();
        int event = packet->par("event").longValue();
        if (role == "sensor") {
            double start = par("eventStart").doubleValue();
            double interval = par("eventInterval").doubleValue();
            event = static_cast<int>(std::floor((simTime().dbl() - start) / interval));
            eventTime = start + event * interval;
            auto address = packet->getTag<L3AddressInd>()->getSrcAddress();
            int port = packet->getTag<L4PortInd>()->getSrcPort();
            transmit("PollResponse", address, port, par("messageLength"), requestTime,
                eventTime, getParentModule()->getIndex(), event);
        }
        else if (role == "broker") {
            // One statically configured subscriber; forward the original event identity/time.
            transmit("Notification", L3AddressResolver().resolve("monitoringApp"), 4000,
                par("messageLength"), requestTime, eventTime, origin, event);
        }
        else if (role == "poller" || role == "subscriber") {
            emit(registerSignal("deliveryDelay"), (simTime() - packet->peekAtFront<ApplicationPacket>()->getTag<CreationTimeTag>()->getCreationTime()).dbl());
            if (role == "poller")
                emit(registerSignal("roundTripTime"), simTime().dbl() - requestTime);
            if (event >= 0 && (!lastEvent.count(origin) || event > lastEvent[origin])) {
                lastEvent[origin] = event;
                observed++;
                emit(registerSignal("eventLatency"), simTime().dbl() - eventTime);
            }
        }
        else
            throw cRuntimeError("Invalid StrategyApp receiver role");
        delete packet;
    }
    void finish() override
    {
        recordScalar("uniqueEventsObserved", observed);
        UdpBasicApp::finish();
    }
};

Define_Module(StrategyApp);
