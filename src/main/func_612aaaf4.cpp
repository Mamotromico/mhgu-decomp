struct Func612aaaf4Data {
    unsigned char pad0[4];
    unsigned char field4;
    unsigned char pad5[3];
    int field8;
    int field12;
};

extern "C" void func_612aaaf4(Func612aaaf4Data *dst, const Func612aaaf4Data *src)
{
    dst->field4 = src->field4;
    dst->field8 = src->field8;
    dst->field12 = src->field12;
}