package com.example.UserAuth.Services;

import com.example.UserAuth.Entity.User;
import com.example.UserAuth.dto.UserDto;

public interface UserService {
 User findByUsername(String username);

 User save(UserDto userDto);

}