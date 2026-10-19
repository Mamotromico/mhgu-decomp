struct func_600c0438_target {
    char pad0[0x3a3];
    unsigned char value;
};

struct func_600c0438_source {
    char pad0[0x1428];
    func_600c0438_target *target;
};

extern "C" void func_600c0438(func_600c0438_source *p) {
    p->target->value = 2;
}