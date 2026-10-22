struct Entry {
    unsigned char pad0[8];
    unsigned char value;
    unsigned char pad1[0x68 - 9];
};

extern "C" unsigned char* func_6130b4b8(Entry* entries, unsigned int index) {
    return index < 10 ? &entries[index].value : 0;
}