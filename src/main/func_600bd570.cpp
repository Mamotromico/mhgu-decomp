struct Target {
    unsigned char pad[0x525];
    unsigned char field;
};

struct Container {
    unsigned char pad[0x1428];
    Target* target;
};

extern "C" Target* func_600bd570(Container* container) {
    Target* target = container->target;
    target->field = 1;
    return target;
}