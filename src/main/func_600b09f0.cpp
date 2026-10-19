struct Buffer_600b09f0 {
    char pad[0x504];
    float value;
};

extern "C" float func_600b09f0(Buffer_600b09f0* p) {
    return p->value;
}