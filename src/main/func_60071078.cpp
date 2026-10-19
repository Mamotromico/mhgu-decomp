struct A {
    unsigned char pad[0x75ec];
    int value;
};

extern "C" int func_60071078(A* p) {
    return p->value + 0x64;
}