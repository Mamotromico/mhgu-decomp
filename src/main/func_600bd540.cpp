struct Outer {
    unsigned char pad[0x1428];
    unsigned char *ptr;
};

extern "C" void func_600bd540(Outer *p) {
    p->ptr[0x5d55] = 1;
}