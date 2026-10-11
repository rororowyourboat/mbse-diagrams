package CommunicationExample {
    part def Participant;
    part def Sender :> Participant;
    part def Receiver :> Participant;
    part def Channel;
    part def Exchange {
        part sender : Sender;
        part channel : Channel;
        part receiver : Receiver;
    }
}
