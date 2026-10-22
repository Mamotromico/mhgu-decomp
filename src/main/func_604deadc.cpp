struct Data_604deadc {
    unsigned char pad_0x00[0x94];
    int field_0x94;
};

extern "C" int func_604deadc(const Data_604deadc *arg)
{
    return arg->field_0x94 == 2;
}