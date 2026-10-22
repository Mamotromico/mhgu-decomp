struct Inner15 {
    char pad0[0x15];
    unsigned char value_15;
};

struct OuterA4 {
    char pad0[0xa4];
    Inner15 *field_a4;
};

extern "C" signed char func_603a358c(OuterA4 *outer)
{
    Inner15 *inner = outer->field_a4;
    return inner ? inner->value_15 : 0;
}