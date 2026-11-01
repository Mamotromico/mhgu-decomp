struct Data_60281948 {
    unsigned char pad[0x508];
    float value;
};

extern "C" int func_60281948(Data_60281948* p) {
    return p->value > 0.0f;
}