struct S_60319588 {
    unsigned char pad_00[0x3c];
    unsigned int field_3c;
    unsigned char pad_40[0x2c];
    unsigned int field_6c;
};

extern "C" unsigned int func_60319588(const S_60319588* s)
{
    unsigned int result = 0;
    if (s->field_6c == 1) {
        result = s->field_3c;
    }
    return result;
}