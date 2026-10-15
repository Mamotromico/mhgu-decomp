struct S {
    char pad[0x10];
    long long val;
};

extern "C" long long func_6134efdc(struct S *s) {
    return s->val;
}