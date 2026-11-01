struct S_603f865c {
    unsigned char pad[0x1c];
    int field;
};

extern "C" int func_603f865c(S_603f865c* s) {
    int f = s->field;
    int result = 1;
    if (f == 3) return result;
    if (f != 6) result = 0;
    return result;
}