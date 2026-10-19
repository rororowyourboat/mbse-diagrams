package NativeViews {
    private import Views::*;

    view def ArchitectureView {
        render asInterconnectionDiagram;
    }
    view architecture : ArchitectureView {
        expose NativeNetwork::Transformer;
    }
    view components {
        expose NativeNetwork::Transformer::*[@SysML::PartUsage and not @SysML::ConnectionUsage];
        render asTreeDiagram;
    }
    view baseline {
        expose NativeExperiment::baseline;
        render asTreeDiagram;
    }
    view analyses {
        expose NativeExperiment::Spectrum;
        expose NativeExperiment::Mechanism;
        expose NativeExperiment::Ablation;
        render asTreeDiagram;
    }
    view empty {
        expose NativeNetwork::Transformer;
        filter false;
    }
}
