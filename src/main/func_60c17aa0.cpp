struct FuncStruct_60c17aa0 {
    unsigned int pad0;
    int f4;
    int f8;
    int fc;
    unsigned char pad10[0xB8];
    unsigned char fc8;
};

extern "C" void func_60c17aa0(FuncStruct_60c17aa0 *s, int a, int b, int c) {
    s->f4 = a;
    s->f8 = c;
    s->fc = b;
    s->fc8 = 1;
}