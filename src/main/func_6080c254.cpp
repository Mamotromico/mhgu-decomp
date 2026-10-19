typedef struct {
    char pad_0x00[0x2c];
    int field_0x2c;
    int field_0x30;
    int field_0x34;
} Func6080c254Arg;

extern "C" void func_6080c254(Func6080c254Arg *p, int a, int b) {
    p->field_0x2c = a;
    p->field_0x30 = b;
    p->field_0x34 = b;
}