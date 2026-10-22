extern "C" {
struct Inner {
    char pad0[0x68];
    int value;
};
struct Outer {
    char pad0[0x75ec];
    Inner *ptr;
};
int func_600711f8(Outer *o, int i) {
    int t = i * 5;
    Inner *p = o->ptr;
    return p->value + t * 2 + 2;
}
}