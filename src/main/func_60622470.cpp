struct Inner {
    char pad0[0x7c];
    unsigned int field_7c;
};

struct Outer {
    char pad0[0x4c];
    unsigned int field_4c;
    Inner* field_50;
};

extern "C" Inner* func_60622470(Outer* p, unsigned int v) {
    p->field_4c = v;
    Inner* q = p->field_50;
    q->field_7c = v;
    return q;
}