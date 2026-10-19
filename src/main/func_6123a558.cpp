struct func_6123a558_struct {
    unsigned char pad[0x40];
    unsigned long long value;
};

extern "C" void func_6123a558(func_6123a558_struct *p, unsigned int lo, unsigned int hi) {
    p->value = (static_cast<unsigned long long>(hi) << 32) | lo;
}