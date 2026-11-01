extern "C" {
struct Inner {
    char pad0[0x8];
    int field8;
};
struct Outer {
    char pad0[0x10];
    unsigned field10;
    char pad14[0x1c - 0x14];
    Inner **field1c;
};
int func_60b1c034(Outer *o, unsigned idx) {
    if (o->field10 <= idx) return 0;
    Inner *p = o->field1c[idx];
    if (!p) return 0;
    return p->field8;
}
}