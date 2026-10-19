extern "C" void func_60622854(char *base, unsigned int index, int value) {
    if (index <= 0x44u) {
        *reinterpret_cast<int *>(base + index * 4 + 0x54) = value;
    }
}