struct func_6130e618_s {
    char pad_0[0x234];
    unsigned char byte_234;
    char pad_235[0x3a3];
    unsigned int word_5d8;
};

extern "C" void func_6130e618(func_6130e618_s *self, unsigned char value) {
    self->byte_234 = value;
    self->word_5d8 |= 0x200;
}