extern "C" void func_60638424(void *);

struct S {
    char pad[0x7c];
    unsigned field_7c;
};

extern "C" void func_60639130(struct S *s, unsigned v, unsigned c) {
    s->field_7c = v;
    if (c == 1)
        func_60638424(s);
}