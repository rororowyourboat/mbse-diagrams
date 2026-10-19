package NativeExperiment {
    private import ScalarValues::*;
    private import NativeNetwork::Transformer;

    part def Experiment {
        attribute modulus : Integer;
        attribute trainingSteps : Integer;
    }
    part baseline : Experiment {
        attribute :>> modulus = 113;
        attribute :>> trainingSteps = 40000;
    }

    analysis def Spectrum {
        subject network : Transformer;
        in attribute checkpointURI : String;
        out attribute observationURI : String;
    }
    analysis def Mechanism {
        subject network : Transformer;
        in attribute checkpointURI : String;
        out attribute observationURI : String;
    }
    analysis def Ablation {
        subject network : Transformer;
        in attribute checkpointURI : String;
        out attribute observationURI : String;
    }
}
