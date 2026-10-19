package NativeViewTypes {
    port def TensorPort;

    part def Source {
        port output : TensorPort;
    }
    part def Transform {
        port input : TensorPort;
        port output : TensorPort;
    }
    part def Add {
        port left : TensorPort;
        port right : TensorPort;
        port output : TensorPort;
    }
}
