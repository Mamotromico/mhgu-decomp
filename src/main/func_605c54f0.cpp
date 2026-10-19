struct FuncStruct
{
    unsigned char pad0[0x4c];
    int field_4c;
    unsigned char pad1[0x3c];
    float field_8c;
    float field_90;
};

extern "C" void func_605c54f0(FuncStruct *p, int value, float a, float b)
{
    p->field_4c = value;
    p->field_8c = a;
    p->field_90 = b;
}