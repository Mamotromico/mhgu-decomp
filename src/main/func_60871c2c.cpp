struct Padded {
    unsigned char pad[0x478];
    float value;
};

extern "C" float func_60871c2c(Padded* p) {
    return p->value;
}