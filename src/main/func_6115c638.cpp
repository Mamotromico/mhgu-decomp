struct Func6115c638Arg {
    unsigned char pad_0x0[0x3328];
    char *field_0x3328;
};

extern "C" void func_6115c638(Func6115c638Arg *arg, float value)
{
    *(float *)(arg->field_0x3328 + 0x474) = value;
}