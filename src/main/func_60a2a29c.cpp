struct S {
    int v;
    char pad[12];
};

struct Outer {
    char pad[0x414];
    S arr[0x1000];
};

extern "C" int func_60a2a29c(struct Outer *o, int i) {
    return o->arr[i].v;
}