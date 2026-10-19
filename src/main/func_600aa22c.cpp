struct Data_600aa22c {
    unsigned char pad[0x7580];
    unsigned char field;
};

extern "C" int func_600aa22c(Data_600aa22c *self) {
    return self->field != 0;
}