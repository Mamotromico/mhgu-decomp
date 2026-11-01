struct S_60c71c5c {
    char pad[0x74];
    unsigned int field_74;
    unsigned int field_78;
};

extern "C" int func_60c71c5c(S_60c71c5c *self, unsigned int mask1, unsigned int mask2) {
    return ((self->field_74 & mask1) != 0) && ((self->field_78 & mask2) != 0);
}