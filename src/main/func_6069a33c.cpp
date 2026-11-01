struct s {
    char pad[0x18];
    signed char **table;
};

extern "C" signed char func_6069a33c(struct s *self, int index, int offset) {
    signed char *entry = self->table[index];
    if (entry == 0)
        return -1;
    return entry[offset + 4];
}