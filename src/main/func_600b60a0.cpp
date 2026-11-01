struct Data {
    int field0;
    int field4;
    int field8;
    int fieldC;
};

extern "C" void func_600b60a0(void *, const Data *src, Data *dst)
{
    dst->field0 = src->field0;
    dst->field4 = src->field4;
    dst->field8 = src->field8;
    dst->fieldC = 0;
}