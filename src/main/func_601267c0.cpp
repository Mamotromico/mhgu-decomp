struct Inner {
    void *field_0;
    void *field_4;
    void *field_8;
    void (*field_c)(void *, void *);
};

struct Arg0 {
    int field_0;
    void *field_4;
};

struct Arg1 {
    Inner *field_0;
};

extern "C" void func_601267c0(Arg0 *arg0, Arg1 *arg1) {
    arg1->field_0->field_c(arg1, arg0->field_4);
}