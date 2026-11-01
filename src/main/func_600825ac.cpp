struct Data_600825ac {
    char pad_0[0x72f4];
    int *field_72f4;
};

extern "C" int func_600825ac(Data_600825ac *self, int index)
{
    int *p = self->field_72f4;
    if (p == 0)
        return 0;
    return p[index] != 0;
}