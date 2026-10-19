package NativeNetwork {
    private import NativeViewTypes::*;
    private import ScalarValues::*;

    part def Transformer {
        attribute modelWidth : Integer = 128;
        attribute heads : Integer = 4;

        part tokens : Source;
        part tokenEmbedding : Transform;
        part positionEmbedding : Source;
        part embeddingAdd : Add;
        part attention : Transform;
        part attentionResidual : Add;
        part mlp : Transform;
        part mlpResidual : Add;
        part outputProjection : Transform;

        connect tokens.output to tokenEmbedding.input;
        connect tokenEmbedding.output to embeddingAdd.left;
        connect positionEmbedding.output to embeddingAdd.right;
        connect embeddingAdd.output to attention.input;
        connect embeddingAdd.output to attentionResidual.left;
        connect attention.output to attentionResidual.right;
        connect attentionResidual.output to mlp.input;
        connect attentionResidual.output to mlpResidual.left;
        connect mlp.output to mlpResidual.right;
        connect mlpResidual.output to outputProjection.input;
    }
}
