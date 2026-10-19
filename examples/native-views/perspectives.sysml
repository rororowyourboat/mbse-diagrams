package ResearchPerspectives {
    private import Views::*;
    private import ScalarValues::*;
    private import NativeNetwork::Transformer;
    private import NativeExperiment::baseline;
    private import NativeExperiment::Spectrum;
    private import NativeExperiment::Mechanism;
    private import NativeExperiment::Ablation;

    doc /* These are model-authored views over one SysML source set. The
         * parameter map records a planned design dependency. The trace map
         * records which planned analysis addresses each hypothesis; it is not
         * evidence that the hypothesis has passed. */

    view def RoleView { render asTreeDiagram; }
    view byRole : RoleView {
        expose NativeNetwork::Transformer::*[@SysML::PartUsage and not @SysML::ConnectionUsage];
    }

    view def DomainView { render asTreeDiagram; }
    view byDomain : DomainView {
        expose NativeNetwork::Transformer::*[@SysML::PartUsage and not @SysML::ConnectionUsage];
        expose NativeExperiment::baseline;
        expose NativeExperiment::Spectrum;
        expose NativeExperiment::Mechanism;
        expose NativeExperiment::Ablation;
    }

    port def ParameterInfluenceSignal;
    part def InfluenceSource {
        attribute modelElement : String;
        port influences : ParameterInfluenceSignal;
    }
    part def InfluenceStep {
        attribute modelElement : String;
        port influencedBy : ~ParameterInfluenceSignal;
        port influences : ParameterInfluenceSignal;
    }
    part def InfluenceTarget {
        attribute modelElement : String;
        port influencedBy : ~ParameterInfluenceSignal;
    }
    part def ParameterInfluenceMap {
        part modulus : InfluenceSource {
            attribute :>> modelElement = "NativeExperiment::baseline::modulus";
        }
        part targetClassSpace : InfluenceStep {
            attribute :>> modelElement = "NativeNetwork::Transformer::outputClasses";
        }
        part outputProjection : InfluenceTarget {
            attribute :>> modelElement = "NativeNetwork::Transformer::outputProjection";
        }

        connect modulus.influences to targetClassSpace.influencedBy;
        connect targetClassSpace.influences to outputProjection.influencedBy;
    }
    view def ParameterInfluenceView { render asInterconnectionDiagram; }
    view parameterInfluence : ParameterInfluenceView {
        expose ParameterInfluenceMap;
    }

    port def AnalysisTraceSignal;
    part def HypothesisNode {
        attribute identifier : String;
        attribute statement : String;
        port evaluatedBy : AnalysisTraceSignal;
    }
    part def AnalysisNode {
        attribute modelElement : String;
        port addresses : ~AnalysisTraceSignal;
        port produces : AnalysisTraceSignal;
    }
    part def PlannedObservationNode {
        attribute description : String;
        port plannedFrom : ~AnalysisTraceSignal;
    }
    part def AnalysisTraceabilityMap {
        part periodicity : HypothesisNode {
            attribute :>> identifier = "H1";
            attribute :>> statement = "Learned embeddings show periodic structure.";
        }
        part spectrum : AnalysisNode {
            attribute :>> modelElement = "NativeExperiment::Spectrum";
        }
        part spectrumObservation : PlannedObservationNode {
            attribute :>> description = "Planned embedding spectrum output";
        }

        part mechanism : HypothesisNode {
            attribute :>> identifier = "H2";
            attribute :>> statement = "The learned computation follows the proposed Fourier mechanism.";
        }
        part mechanismAnalysis : AnalysisNode {
            attribute :>> modelElement = "NativeExperiment::Mechanism";
        }
        part mechanismObservation : PlannedObservationNode {
            attribute :>> description = "Planned mechanism analysis output";
        }

        part causalReliance : HypothesisNode {
            attribute :>> identifier = "H3";
            attribute :>> statement = "Predictions rely on the identified Fourier frequencies.";
        }
        part ablation : AnalysisNode {
            attribute :>> modelElement = "NativeExperiment::Ablation";
        }
        part ablationObservation : PlannedObservationNode {
            attribute :>> description = "Planned frequency ablation output";
        }

        connect periodicity.evaluatedBy to spectrum.addresses;
        connect spectrum.produces to spectrumObservation.plannedFrom;
        connect mechanism.evaluatedBy to mechanismAnalysis.addresses;
        connect mechanismAnalysis.produces to mechanismObservation.plannedFrom;
        connect causalReliance.evaluatedBy to ablation.addresses;
        connect ablation.produces to ablationObservation.plannedFrom;
    }
    view def AnalysisTraceabilityView { render asInterconnectionDiagram; }
    view analysisTraceability : AnalysisTraceabilityView {
        expose AnalysisTraceabilityMap;
    }
}
