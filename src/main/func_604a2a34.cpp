struct Element {
    char pad[0xb8];
};

struct Target {
    char pad[0x1408];
    float value;
};

extern "C" struct Element *func_604a2a34(struct Element *base, int index) {
    struct Element *e = base + index;
    struct Target *t = (struct Target *)e;
    t->value = 100.0f;
    return e;
}