struct Payload {
    char pad_0[0x14];
    int field_14;
    int field_18;
};

extern "C" void func_60864b70(Payload* self, int value)
{
    self->field_14 = 0;
    self->field_18 = value;
}